# Changelog

## [2.1.0](https://github.com/ibis-project/ibis-bigquery/compare/v2.0.0...v2.1.0) (2022-03-15)


### Features

* Raise better error message when incorrect dataset is supplied [#113](https://github.com/ibis-project/ibis-bigquery/issues/113) ([#115](https://github.com/ibis-project/ibis-bigquery/issues/115)) ([dc474af](https://github.com/ibis-project/ibis-bigquery/commit/dc474af94bb8590c9acf3ec3f94634f366349580))


### Bug Fixes

* avoid deprecated "out-of-band" authentication flow ([#116](https://github.com/ibis-project/ibis-bigquery/issues/116)) ([9dc5808](https://github.com/ibis-project/ibis-bigquery/commit/9dc580800d607b809433bb2a3f2da2ba43b2f679))


### Dependencies

* fix minimum ibis-framework dependency ([b8834ce](https://github.com/ibis-project/ibis-bigquery/commit/b8834ce58453a09d790f44eb73f98319f17f84fa))

## [2.0.0](https://www.github.com/ibis-project/ibis-bigquery/compare/v0.1.1...v2.0.0) (2021-12-02)


### ⚠ BREAKING CHANGES

* support ibis 2.x, drop ibis 1.x (#93)

### Features

* support ibis 2.x, drop ibis 1.x ([#93](https://www.github.com/ibis-project/ibis-bigquery/issues/93)) ([780d071](https://www.github.com/ibis-project/ibis-bigquery/commit/780d07168758571d582e8a679e194ac8de33b36b))


### Miscellaneous Chores

* release 2.0.0 ([c5c3f24](https://www.github.com/ibis-project/ibis-bigquery/commit/c5c3f2414dbb2046b5e3bdb14204b6440c9a772b))

## [1.0.0](https://www.github.com/ibis-project/ibis-bigquery/compare/v0.1.1...v1.0.0) (2021-12-02)

### Bug Fixes

* substr fails to compile ([#95](https://github.com/ibis-project/ibis-bigquery/pull/95))) 

## [0.1.1](https://www.github.com/ibis-project/ibis-bigquery/compare/v0.1.0...v0.1.1) (2021-04-28)


### Dependencies

* support pyarrow 4 ([#45](https://www.github.com/ibis-project/ibis-bigquery/issues/45)) ([0346821](https://www.github.com/ibis-project/ibis-bigquery/commit/03468217650d639d304c91e00ca4507828cfcfc4))

## 0.1.0 (2021-04-27)


### Features

* add `entry_points` so that ibis 2 can discover this backend ([#38](https://www.github.com/ibis-project/ibis-bigquery/issues/38)) ([c3d188e](https://www.github.com/ibis-project/ibis-bigquery/commit/c3d188e107176c7fff6e7bce572330797cb3e2bc))
* add `ibis_bigquery.__version__` property ([#29](https://www.github.com/ibis-project/ibis-bigquery/issues/29)) ([58d624a](https://www.github.com/ibis-project/ibis-bigquery/commit/58d624abaaa9db4106241128559e28b5c2a2e715))
* add `ibis_bigquery.connect` and `ibis_bigquery.compile` functions ([#37](https://www.github.com/ibis-project/ibis-bigquery/issues/37)) ([7348bf2](https://www.github.com/ibis-project/ibis-bigquery/commit/7348bf2daea0f99e0e46d77cdcd8863f4274ab8b))
* check for negative values before doing substr ([#32](https://github.com/ibis-project/ibis-bigquery/pull/32)) ([d515184](https://github.com/ibis-project/ibis-bigquery/commit/d51518427b3178939ff40fd6a62f8298e71b57a0))


### Bug Fixes

* compatibility with ibis 1.4.0 (and possibly 1.2, 1.3) ([#31](https://www.github.com/ibis-project/ibis-bigquery/issues/31)) ([b6bbfbe](https://www.github.com/ibis-project/ibis-bigquery/commit/b6bbfbe412ec017e441ecb730c590dfccadfbd84))
* update UDF to support Python 3.8+ AST ([#25](https://www.github.com/ibis-project/ibis-bigquery/issues/25)) ([3d9b2cb](https://www.github.com/ibis-project/ibis-bigquery/commit/3d9b2cbda4ea091bfa1442a306c4ef9271fb3a4c))
* use TIMESTAMP_SUB for TimstampSub operation ([#40](https://www.github.com/ibis-project/ibis-bigquery/issues/40)) ([4c5cb57](https://www.github.com/ibis-project/ibis-bigquery/commit/4c5cb5769497eece2913ec567057b6d440c0922b))
