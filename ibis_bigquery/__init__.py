"""BigQuery public API."""
import warnings
from typing import Optional, Tuple

import google.auth.credentials
import google.cloud.bigquery as bq
import ibis.expr.schema as sch
import ibis.expr.types as ir
import pydata_google_auth
from google.api_core.exceptions import NotFound
from ibis.backends.base.sql import BaseSQLBackend
from pydata_google_auth import cache

from . import version as ibis_bigquery_version
from .client import (
    BigQueryCursor,
    BigQueryDatabase,
    BigQueryTable,
    _create_client_info,
    bigquery_field_to_ibis_dtype,
    bigquery_param,
    parse_project_and_dataset,
    rename_partitioned_column,
)
from .compiler import BigQueryCompiler

try:
    from .udf import udf  # noqa F401
except ImportError:
    pass


__version__: str = ibis_bigquery_version.__version__

SCOPES = ["https://www.googleapis.com/auth/bigquery"]
EXTERNAL_DATA_SCOPES = [
    "https://www.googleapis.com/auth/bigquery",
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/drive",
]
CLIENT_ID = "546535678771-gvffde27nd83kfl6qbrnletqvkdmsese.apps.googleusercontent.com"
CLIENT_SECRET = "iU5ohAF2qcqrujegE3hQ1cPt"


class Backend(BaseSQLBackend):
    name = "bigquery"
    compiler = BigQueryCompiler
    database_class = BigQueryDatabase
    table_class = BigQueryTable

    def connect(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = "",
        credentials: Optional[google.auth.credentials.Credentials] = None,
        application_name: Optional[str] = None,
        auth_local_webserver: bool = True,
        auth_external_data: bool = False,
        auth_cache: str = "default",
        partition_column: Optional[str] = "PARTITIONTIME",
    ) -> "Backend":
        """Create a :class:`Backend` for use with Ibis.

        Parameters
        ----------
        project_id : str
            A BigQuery project id.
        dataset_id : str
            A dataset id that lives inside of the project indicated by
            `project_id`.
        credentials : google.auth.credentials.Credentials
        application_name : str
            A string identifying your application to Google API endpoints.
        auth_local_webserver : bool
            Use a local webserver for the user authentication.  Binds a
            webserver to an open port on localhost between 8080 and 8089,
            inclusive, to receive authentication token. If not set, defaults
            to False, which requests a token via the console.
        auth_external_data : bool
            Authenticate using additional scopes required to `query external
            data sources
            <https://cloud.google.com/bigquery/external-data-sources>`_,
            such as Google Sheets, files in Google Cloud Storage, or files in
            Google Drive. If not set, defaults to False, which requests the
            default BigQuery scopes.
        auth_cache : str
            Selects the behavior of the credentials cache.

            ``'default'``
                Reads credentials from disk if available, otherwise
                authenticates and caches credentials to disk.

            ``'reauth'``
                Authenticates and caches credentials to disk.

            ``'none'``
                Authenticates and does **not** cache credentials.

            Defaults to ``'default'``.
        partition_column : str
            Identifier to use instead of default ``_PARTITIONTIME`` partition
            column. Defaults to ``'PARTITIONTIME'``.

        Returns
        -------
        Backend

        """
        default_project_id = ""

        if credentials is None:
            scopes = SCOPES
            if auth_external_data:
                scopes = EXTERNAL_DATA_SCOPES

            if auth_cache == "default":
                credentials_cache = cache.ReadWriteCredentialsCache(
                    filename="ibis.json"
                )
            elif auth_cache == "reauth":
                credentials_cache = cache.WriteOnlyCredentialsCache(
                    filename="ibis.json"
                )
            elif auth_cache == "none":
                credentials_cache = cache.NOOP
            else:
                raise ValueError(
                    f"Got unexpected value for auth_cache = '{auth_cache}'. "
                    "Expected one of 'default', 'reauth', or 'none'."
                )

            credentials, default_project_id = pydata_google_auth.default(
                scopes,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                credentials_cache=credentials_cache,
                use_local_webserver=auth_local_webserver,
            )

        project_id = project_id or default_project_id

        new_backend = self.__class__()

        (
            new_backend.data_project,
            new_backend.billing_project,
            new_backend.dataset,
        ) = parse_project_and_dataset(project_id, dataset_id)

        new_backend.client = bq.Client(
            project=new_backend.billing_project,
            credentials=credentials,
            client_info=_create_client_info(application_name),
        )
        new_backend.partition_column = partition_column

        return new_backend

    def _parse_project_and_dataset(self, dataset) -> Tuple[str, str]:
        if not dataset and not self.dataset:
            raise ValueError("Unable to determine BigQuery dataset.")
        project, _, dataset = parse_project_and_dataset(
            self.billing_project,
            dataset or "{}.{}".format(self.data_project, self.dataset),
        )
        return project, dataset

    @property
    def project_id(self):
        return self.data_project

    @property
    def dataset_id(self):
        return self.dataset

    def table(self, name, database=None) -> ir.TableExpr:
        t = super().table(name, database=database)
        table_id = self._fully_qualified_name(name, database)
        bq_table = self.client.get_table(table_id)
        return rename_partitioned_column(t, bq_table, self.partition_column)

    def _fully_qualified_name(self, name, database):
        default_project, default_dataset = self._parse_project_and_dataset(database)
        parts = name.split(".")
        if len(parts) == 3:
            return name
        elif len(parts) == 2:
            return "{}.{}".format(default_project, name)
        elif len(parts) == 1:
            return "{}.{}.{}".format(default_project, default_dataset, name)
        raise ValueError("Got too many components in table name: {}".format(name))

    def _get_schema_using_query(self, limited_query):
        with self._execute(limited_query, results=True) as cur:
            # resets the state of the cursor and closes operation
            names, ibis_types = self._adapt_types(cur.description)
        return sch.Schema(names, ibis_types)

    def _get_table_schema(self, qualified_name):
        dataset, table = qualified_name.rsplit(".", 1)
        assert dataset is not None, "dataset is None"
        return self.get_schema(table, database=dataset)

    def _adapt_types(self, descr):
        names = []
        adapted_types = []
        for col in descr:
            names.append(col.name)
            typename = bigquery_field_to_ibis_dtype(col)
            adapted_types.append(typename)
        return names, adapted_types

    def _execute(self, stmt, results=True, query_parameters=None):
        job_config = bq.job.QueryJobConfig()
        job_config.query_parameters = query_parameters or []
        job_config.use_legacy_sql = False  # False by default in >=0.28
        query = self.client.query(
            stmt, job_config=job_config, project=self.billing_project
        )
        query.result()  # blocks until finished
        return BigQueryCursor(query)

    def raw_sql(self, query: str, results=False, params=None):
        query_parameters = [
            bigquery_param(param, value) for param, value in (params or {}).items()
        ]
        return self._execute(query, results=results, query_parameters=query_parameters)

    @property
    def current_database(self) -> str:
        return self.dataset

    def database(self, name=None):
        if name is None and not self.dataset:
            raise ValueError(
                "Unable to determine BigQuery dataset. Call "
                "client.database('my_dataset') or set_database('my_dataset') "
                "to assign your client a dataset."
            )
        return self.database_class(name or self.dataset, self)

    def execute(self, expr, params=None, limit="default", **kwargs):
        """Compile and execute the given Ibis expression.

        Compile and execute Ibis expression using this backend client
        interface, returning results in-memory in the appropriate object type

        Parameters
        ----------
        expr : Expr
        limit : int, default None
          For expressions yielding result yets; retrieve at most this number of
          values/rows. Overrides any limit already set on the expression.
        params : not yet implemented
        kwargs : Backends can receive extra params. For example, clickhouse
            uses this to receive external_tables as dataframes.

        Returns
        -------
        output : input type dependent
          Table expressions: pandas.DataFrame
          Array expressions: pandas.Series
          Scalar expressions: Python scalar value
        """
        # TODO: upstream needs to pass params to raw_sql, I think.
        kwargs.pop("timecontext", None)
        query_ast = self.compiler.to_ast_ensure_limit(expr, limit, params=params)
        sql = query_ast.compile()
        self._log(sql)
        cursor = self.raw_sql(sql, params=params, **kwargs)
        schema = self.ast_schema(query_ast, **kwargs)
        result = self.fetch_from_cursor(cursor, schema)

        if hasattr(getattr(query_ast, "dml", query_ast), "result_handler"):
            result = query_ast.dml.result_handler(result)

        return result

    def exists_database(self, name):
        """
        Return whether a database name exists in the current connection.

        Deprecated in Ibis 2.0. Use `name in client.list_databases()` instead.
        """
        warnings.warn(
            "`client.exists_database(name)` is deprecated, and will be "
            "removed in a future version of Ibis. Use "
            "`name in client.list_databases()` instead.",
            FutureWarning,
        )

        project, dataset = self._parse_project_and_dataset(name)
        client = self.client
        dataset_ref = client.dataset(dataset, project=project)
        try:
            client.get_dataset(dataset_ref)
        except NotFound:
            return False
        else:
            return True

    def exists_table(self, name: str, database: str = None) -> bool:
        """
        Return whether a table name exists in the database.

        Deprecated in Ibis 2.0. Use `name in client.list_tables()` instead.
        """
        warnings.warn(
            "`client.exists_table(name)` is deprecated, and will be "
            "removed in a future version of Ibis. Use "
            "`name in client.list_tables()` instead.",
            FutureWarning,
        )

        table_id = self._fully_qualified_name(name, database)
        client = self.client
        try:
            client.get_table(table_id)
        except NotFound:
            return False
        else:
            return True

    def fetch_from_cursor(self, cursor, schema):
        df = cursor.query.to_dataframe()
        return schema.apply_to(df)

    def get_schema(self, name, database=None):
        table_id = self._fully_qualified_name(name, database)
        table_ref = bq.TableReference.from_string(table_id)
        bq_table = self.client.get_table(table_ref)
        return sch.infer(bq_table)

    def list_databases(self, like=None):
        results = [
            dataset.dataset_id
            for dataset in self.client.list_datasets(project=self.data_project)
        ]
        return self._filter_with_like(results, like)

    def list_tables(self, like=None, database=None):
        project, dataset = self._parse_project_and_dataset(database)
        dataset_ref = bq.DatasetReference(project, dataset)
        result = [table.table_id for table in self.client.list_tables(dataset_ref)]
        return self._filter_with_like(result, like)

    def set_database(self, name):
        self.data_project, self.dataset = self._parse_project_and_dataset(name)

    @property
    def version(self):
        return bq.__version__


def compile(expr, params=None, **kwargs):
    """Compile an expression for BigQuery.
    Returns
    -------
    compiled : str
    See Also
    --------
    ibis.expr.types.Expr.compile
    """
    backend = Backend()
    return backend.compile(expr, params=params, **kwargs)


def connect(
    project_id: Optional[str] = None,
    dataset_id: str = "",
    credentials: Optional[google.auth.credentials.Credentials] = None,
    application_name: Optional[str] = None,
    auth_local_webserver: bool = False,
    auth_external_data: bool = False,
    auth_cache: str = "default",
    partition_column: Optional[str] = "PARTITIONTIME",
) -> Backend:
    """Create a :class:`Backend` for use with Ibis.

    Parameters
    ----------
    project_id : str
        A BigQuery project id.
    dataset_id : str
        A dataset id that lives inside of the project indicated by
        `project_id`.
    credentials : google.auth.credentials.Credentials
    application_name : str
        A string identifying your application to Google API endpoints.
    auth_local_webserver : bool
        Use a local webserver for the user authentication.  Binds a
        webserver to an open port on localhost between 8080 and 8089,
        inclusive, to receive authentication token. If not set, defaults
        to False, which requests a token via the console.
    auth_external_data : bool
        Authenticate using additional scopes required to `query external
        data sources
        <https://cloud.google.com/bigquery/external-data-sources>`_,
        such as Google Sheets, files in Google Cloud Storage, or files in
        Google Drive. If not set, defaults to False, which requests the
        default BigQuery scopes.
    auth_cache : str
        Selects the behavior of the credentials cache.

        ``'default'``
            Reads credentials from disk if available, otherwise
            authenticates and caches credentials to disk.

        ``'reauth'``
            Authenticates and caches credentials to disk.

        ``'none'``
            Authenticates and does **not** cache credentials.

        Defaults to ``'default'``.
    partition_column : str
        Identifier to use instead of default ``_PARTITIONTIME`` partition
        column. Defaults to ``'PARTITIONTIME'``.

    Returns
    -------
    Backend

    """
    backend = Backend()
    return backend.connect(
        project_id=project_id,
        dataset_id=dataset_id,
        credentials=credentials,
        application_name=application_name,
        auth_local_webserver=auth_local_webserver,
        auth_external_data=auth_external_data,
        auth_cache=auth_cache,
        partition_column=partition_column,
    )


__all__ = [
    "__version__",
    "Backend",
    "compile",
    "connect",
]
