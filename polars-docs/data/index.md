# Polars Documentation Index

> Source: https://github.com/pola-rs/polars
> Last updated: 2025-12-08
> Commit: 1ef5ef1336b2fb3d2bbdf1e3bf3e05b6ada65eb8

---

## Expressions (Priority Section)

*The heart of Polars' DSL - lazy representations of data transformations that can be composed, optimized, and parallelized.*

### Overview & Concepts
- **Expressions Index** `user-guide/expressions/index.md` - Overview of all expression types: essentials (basic ops, expansion, casting), data type namespaces (strings, lists, categoricals, structs, missing data), operation types (aggregation, window functions, folds), and UDFs

### Essential Operations
- **Basic Operations** `user-guide/expressions/basic-operations.md` - Foundational expression operations:
  - *Arithmetic*: `+`, `-`, `*`, `/`, `//`, `%`, `**` between series or with literals (literals broadcast); null propagates
  - *Comparisons*: `<`, `<=`, `>`, `>=`, `==`, `!=` with operator overloading
  - *Boolean/Bitwise*: `&` (and), `|` (or), `~` (not), `^` (xor) - Python uses these for Boolean due to keyword restrictions
  - *Counting*: `n_unique` (exact), `approx_n_unique` (HyperLogLog++), `value_counts` (returns Struct), `unique`, `unique_counts`
  - *Conditionals*: `when(...).then(...).otherwise(...)` - ternary operator equivalent, chainable for elif-style logic

- **Expression Expansion** `user-guide/expressions/expression-expansion.md` - Write one expression that expands to multiple columns:
  - *By column names*: `pl.col("a", "b", "c")` - explicit list of columns
  - *By data type*: `pl.col(pl.Float64)` or `pl.col(pl.Float64, pl.Int64)` - all columns matching type(s)
  - *By regex*: `pl.col("^price_.*$")` - pattern must start with `^` and end with `$`
  - *All columns*: `pl.all()` (preferred) or `pl.col("*")`
  - *Excluding*: `pl.all().exclude("col")` or `pl.col(pl.Float64).exclude("price")`
  - *Renaming*: `alias` (single), `name.prefix/suffix` (multiple), `name.map` (dynamic with callable)
  - *Programmatic generation*: Use generators/list comprehensions instead of for-loops with `with_columns`
  - *Selectors* (`polars.selectors`): `cs.numeric()`, `cs.temporal()`, `cs.string()`, `cs.starts_with()`, `cs.ends_with()`, `cs.contains()`, `cs.matches()` - combine with `|`, `&`, `-`, `^`, `~`; use `as_expr()` to disambiguate operators

- **Casting** `user-guide/expressions/casting.md` - Type conversion with `cast()`:
  - *Strict mode* (default): errors on conversion failure; `strict=False` converts failures to `null`
  - *Numeric*: float<->int (truncates), downcasting for memory (check precision limits!)
  - *String<->Numeric*: parse strings to numbers, format numbers as strings
  - *Boolean*: 0=False, non-zero=True; True=1, False=0
  - *Temporal*: internal representation is time units since epoch; use `dt.to_string`/`str.to_datetime` for formatting with chrono syntax

### Data Type Namespaces

- **Strings** `user-guide/expressions/strings.md` - `str` namespace with 40+ functions:
  - *Length*: `str.len_bytes` (faster for ASCII), `str.len_chars`
  - *Pattern checking*: `str.contains` (regex or literal), `str.starts_with`, `str.ends_with`
  - *Extraction*: `str.extract` (single capture group), `str.extract_all` (returns List)
  - *Replacement*: `str.replace` (first match), `str.replace_all` (all non-overlapping)
  - *Case conversion*: `str.to_lowercase`, `str.to_titlecase`, `str.to_uppercase`
  - *Stripping*: `str.strip_chars` (set of chars), `str.strip_prefix`/`str.strip_suffix` (exact substring)
  - *Slicing*: `str.slice(offset, length)`, `str.head(n)`, `str.tail(n)`
  - *Note*: Regex syntax follows Rust `regex` crate (different from Python `re`)

- **Lists and Arrays** `user-guide/expressions/lists-and-arrays.md` - Homogeneous container types:
  - *List vs Array*: Array has fixed shape (more efficient), List has variable length (more flexible)
  - *Prefer Array* when shape is known; use List when lengths vary or need list-only functions
  - *Namespace migration*: `arr` was for lists pre-1.0, now `arr` is for Array, `list` is for List
  - *Creating lists*: `str.split`, aggregations in `group_by`
  - *Operations*: `list.head`, `list.tail`, `list.slice`, `list.len`, `list.sum`, `list.mean`
  - *Element-wise*: `list.eval(pl.element().some_expr())` - apply expression to each element
  - *Aggregation*: `list.agg` returns scalar when possible; `list.eval` always returns list
  - *Row-wise*: `pl.concat_list(...)` with `list.eval` for horizontal operations across columns

- **Categorical Data and Enums** `user-guide/expressions/categorical-data-and-enums.md` - Efficient string encoding:
  - *Enum*: Categories known upfront, ordered, consistent encoding across columns - PREFERRED
  - *Categorical*: Categories inferred at runtime, needs StringCache for cross-column operations
  - *StringCache*: Global cache ensuring consistent encoding - `with pl.StringCache():` context manager
  - *Performance*: Physical integer storage enables fast comparisons and joins vs string operations
  - *Comparison*: Enum uses category order; Categorical uses lexical comparison (since 1.32.0)
  - *Warning*: Combining categoricals without StringCache causes expensive re-encoding

- **Structs** `user-guide/expressions/structs.md` - Composite type storing multiple fields:
  - *Like a TypedDict*: Named fields with types, stored in single column
  - *Common source*: `value_counts` returns Struct; dictionaries infer to Struct
  - *Unnesting*: `df.unnest("struct_col")` expands fields to separate columns
  - *Field access*: `struct.field("name")` extracts single field
  - *Renaming*: `struct.rename_fields(["new_name1", "new_name2"])`
  - *Use cases*: Duplicate detection (`pl.struct("a", "b").is_duplicated()`), multi-column ranking, passing multiple columns to UDFs via `map_elements`

- **Missing Data** `user-guide/expressions/missing-data.md` - Handling `null` values:
  - *null vs NaN*: `null` is missing data (any type); `NaN` is valid float value
  - *Metadata*: Validity bitmap tracks nulls efficiently (bit-packed, O(1) `null_count`)
  - *Detection*: `is_null`, `null_count` (cheap operations using bitmap)
  - *Filling*: `fill_null(literal)`, `fill_null(expression)`, `fill_null(strategy="forward"|"backward")`, `interpolate`
  - *NaN handling*: `is_nan`, `fill_nan` - aggregations skip null but propagate NaN; convert NaN to null with `fill_nan(None)`

### Aggregation & Grouping

- **Aggregation** `user-guide/expressions/aggregation.md` - `group_by` context:
  - *Basic*: `df.group_by("col").agg(expressions)` - no limit on number of expressions
  - *Implicit aggregation*: Just column name creates list; explicit `.first()`, `.last()`, `.mean()`, `.sum()`, `.len()`
  - *Conditionals in agg*: `pl.col("x").filter(pl.col("y") > 0).mean()` - filter within groups
  - *Nested grouping*: `group_by(["col1", "col2"])` for multi-level grouping
  - *Sorting in groups*: Use `.sort()` or `.sort_by()` within expressions; avoids pre-sorting dataframe
  - *Performance warning*: Avoid lambdas/custom Python functions - kills parallelization (GIL)

- **Window Functions** `user-guide/expressions/window-functions.md` - Aggregations within `select`/`with_columns`:
  - *Syntax*: `expression.over("group_col")` or `expression.over(["col1", "col2"])`
  - *Difference from group_by*: Returns same number of rows as input (broadcasts aggregation results)
  - *mapping_strategy parameter*:
    - `"group_to_rows"` (default): Results mapped back to original row positions
    - `"explode"`: Faster, but reorders rows to group members together
    - `"join"`: Aggregates to list, repeats list for all group members
  - *Scalar broadcasting*: Aggregations like `.mean().over("group")` broadcast scalar to all group rows
  - *Use cases*: Ranking within groups, computing group statistics alongside original data

- **Folds** `user-guide/expressions/folds.md` - Horizontal operations across columns:
  - *`pl.fold(acc, function, exprs)`*: Apply binary function across columns, like `functools.reduce`
  - *Accumulator*: Initial value; typically identity element (0 for sum, 1 for product)
  - *Built-in alternatives*: `sum_horizontal`, `mean_horizontal`, `min_horizontal` - use these when available
  - *Conditionals*: `pl.fold(pl.lit(True), lambda a, b: a & b, pl.all())` - check condition across all columns
  - *String concatenation*: Use `concat_str` instead of fold (avoids quadratic complexity)

### User-Defined Functions

- **User-Defined Python Functions** `user-guide/expressions/user-defined-python-functions.md` - Escape hatch for custom logic:
  - *`map_elements`*: Calls function on each value individually (slow, use sparingly)
  - *`map_batches`*: Passes full Series to function (better performance)
  - *NumPy ufuncs*: Best performance - use `np.log`, `np.exp`, etc. directly on expressions
  - *Numba `@guvectorize`*: Compile custom functions to machine code for near-native speed
  - *Missing data*: Generalized ufuncs error on nulls; fill or drop nulls first
  - *Multiple columns*: Create Struct, access fields in function with `x["field_name"]`
  - *`is_elementwise=True`*: Enables streaming for memory efficiency (only for true element-wise ops)
  - *Return types*: Inferred from first non-null; override with `return_dtype` parameter

- **NumPy Functions** `user-guide/expressions/numpy-functions.md` - NumPy interoperability:
  - *Ufunc support*: `np.exp`, `np.cos`, `np.log`, etc. work directly on Polars expressions
  - *Zero-copy*: Series converted to NumPy array with minimal overhead
  - *Caveat*: NumPy doesn't understand Polars null bitmask; generalized ufuncs may give wrong results with nulls

---

## Transformations (Priority Section)

*Operations that reshape, combine, or restructure dataframes.*

### Overview
- **Transformations Index** `user-guide/transformations/index.md` - Links to joins, concatenation, pivot, unpivot, and time series operations

### Joins

- **Joins** `user-guide/transformations/joins.md` - Combining dataframes by matching rows:

  #### Equi Joins (match on key equality)
  - *Inner* `join(..., how="inner")`: Only rows with matches in both dataframes (default)
  - *Left* `join(..., how="left")`: All left rows + matching right rows; non-matches get null
  - *Right* `join(..., how="right")`: All right rows + matching left rows; non-matches get null
  - *Full* `join(..., how="full")`: All rows from both; non-matches get null on opposite side
  - *Semi* `join(..., how="semi")`: Left rows that have a match (no columns from right added)
  - *Anti* `join(..., how="anti")`: Left rows that have NO match (filters based on right)

  #### Key Expressions
  - *Simple*: `join(other, on="key_col")` when column names match
  - *Different names*: `join(other, left_on="left_col", right_on="right_col")`
  - *Expressions*: `join(other, left_on=pl.col("name").str.to_lowercase(), right_on=pl.col("NAME").str.to_lowercase())` - dynamic key computation

  #### Column Handling
  - *`coalesce` parameter*: `True` merges key columns; `False` keeps both (auto-determined by strategy)
  - *Suffix*: Duplicate non-key columns get `_right` suffix by default

  #### Non-Equi Joins
  - *`join_where(predicates)`*: Match rows where predicate(s) are true; predicates AND-combined
  - *Use case*: Find all items where `player.cash >= item.price`

  #### Asof Joins
  - *`join_asof`*: Match on nearest key (not exact); like left join with proximity matching
  - *`strategy="backward"` (default)*: Match to most recent value <= join key
  - *`strategy="forward"`*: Match to next value >= join key
  - *`by` parameter*: Exact match on grouping column before asof matching
  - *`tolerance` parameter*: Maximum allowed distance for match (e.g., `"1m"` for 1 minute)
  - *Use case*: Stock trades matched to most recent quote

  #### Cartesian Product
  - *`join(..., how="cross")`*: All combinations of left and right rows; no key needed

### Concatenation

- **Concatenation** `user-guide/transformations/concatenation.md` - Combining dataframes without matching:
  - *Vertical* `pl.concat([df1, df2], how="vertical")`: Stack rows (same columns required)
  - *Horizontal* `pl.concat([df1, df2], how="horizontal")`: Add columns side-by-side (no overlapping names)
  - *Diagonal* `pl.concat([df1, df2], how="diagonal")`: Combine rows AND columns; fills gaps with null
  - *Rechunking*: `rechunk=True` makes memory contiguous (slower concat, faster subsequent ops)

### Reshaping

- **Pivot** `user-guide/transformations/pivot.md` - Long to wide format:
  - *Syntax*: `df.pivot(on="column_to_spread", index="row_identifier", values="values_column")`
  - *Aggregation*: Required when multiple values per cell - `first`, `last`, `sum`, `min`, `max`, `mean`, `median`, `len`
  - *Lazy caveat*: Pivot needs data to determine schema; use `collect().pivot().lazy()` in lazy pipelines

- **Unpivot** `user-guide/transformations/unpivot.md` - Wide to long format:
  - *Syntax*: `df.unpivot(on=["col1", "col2"], index="id_col")`
  - *Result*: `variable` column (original column names) and `value` column (values)
  - *Works in lazy*: Schema determinable without data

### Time Series

- **Parsing Temporal Data** `user-guide/transformations/time-series/parsing.md` - Creating datetime columns:
  - *Data types*: `Date` (days since epoch), `Datetime` (configurable unit: ns/us/ms), `Duration`, `Time` (nanoseconds since midnight)
  - *From CSV*: `read_csv(..., try_parse_dates=True)` - auto-infers; `infer_schema_length` controls sample size
  - *From strings*: `str.to_date`, `str.to_datetime` - specify format with chrono syntax
  - *Feature extraction*: `dt.year`, `dt.month`, `dt.day`, `dt.hour`, `dt.minute`, `dt.second`, `dt.weekday`
  - *Mixed offsets*: Parse with `utc=True`, then `dt.convert_time_zone`

- **Filtering Time Series** `user-guide/transformations/time-series/filter.md` - Date-based row selection:
  - *Single date*: `filter(pl.col("date") == datetime(2023, 1, 1))` - use Python datetime objects
  - *Date range*: `filter(pl.col("date").is_between(start, end))`
  - *Negative dates*: Use `dt.year()` attributes instead of Python datetime (doesn't support negative years)

- **Grouping & Rolling** `user-guide/transformations/time-series/rolling.md` - Temporal aggregations:
  - *`group_by_dynamic`*: Fixed-interval windows over time
    - `every`: Window start interval (e.g., `"1mo"`, `"1w"`, `"1d"`)
    - `period`: Window duration (defaults to `every`); can create overlapping windows
    - `offset`: Shift window start times
    - `truncate`: True=window start date; False=first data point date
  - *`rolling`*: Variable windows determined by data values; one group per row
  - *Combining*: Can add `group_by` columns alongside dynamic/rolling grouping
  - *Note*: Data MUST be sorted by time column ascending!

- **Resampling** `user-guide/transformations/time-series/resampling.md` - Changing time frequency:
  - *Downsampling*: Use `group_by_dynamic` to aggregate to lower frequency
  - *Upsampling*: `df.upsample(time_column="date", every="15m")` - creates rows at new frequency
  - *Fill strategies*: `fill_null(strategy="forward")` or `interpolate` after upsampling

- **Time Zones** `user-guide/transformations/time-series/timezones.md` - Timezone handling:
  - *Representations*: `None` (naive), `"UTC"`, or `"Area/Location"` format (e.g., `"Asia/Kathmandu"`)
  - *Setting timezone*: `dt.replace_time_zone("UTC")` - interprets naive as specified zone
  - *Converting*: `dt.convert_time_zone("America/New_York")` - shifts time value
  - *Avoid*: Fixed offsets like `+02:00` - use IANA database names for DST handling

---

## Core Concepts

### Expressions & Contexts
- **Expressions and Contexts** `user-guide/concepts/expressions-and-contexts.md` - Polars DSL fundamentals:
  - *Expression*: Lazy computation representation; can be stored, printed, composed
  - *Contexts*: Where expressions execute - `select`, `with_columns`, `filter`, `group_by`
  - *`select`*: Returns only specified columns; expressions must produce same-length series
  - *`with_columns`*: Adds/replaces columns while keeping originals; must match original length
  - *`filter`*: Rows where Boolean expression is True
  - *`group_by`*: Groups by expression value(s); `agg` applies expressions to groups

### Data Types & Structures
- **Data Types and Structures** `user-guide/concepts/data-types-and-structures.md` - Polars building blocks:
  - *Series*: 1D homogeneous container with name and dtype
  - *DataFrame*: 2D heterogeneous structure; uniquely named Series
  - *Schema*: Mapping of column names to data types; can be explicit or inferred
  - *Inspection*: `head`, `tail`, `sample`, `glimpse` (Python), `describe`
  - *Arrow backing*: Uses Arrow Columnar Format for zero-copy interop
  - *Full type table*: Boolean, Int8-128, UInt8-128, Float16/32/64, Decimal, String, Binary, Date, Time, Datetime, Duration, Array, List, Object, Categorical, Enum, Struct, Null

---

## Other Sections (Quick Reference)

### Getting Started
- **Getting Started** `user-guide/getting-started.md` - First steps with Polars
- **Installation** `user-guide/installation.md` - Installing Polars for Python/Rust

### Lazy API
- **Lazy API** `user-guide/lazy/index.md` - Deferred execution and query optimization
- **Using the Lazy API** `user-guide/lazy/using.md` - `lazy()`, `collect()`, working with LazyFrames
- **Optimizations** `user-guide/lazy/optimizations.md` - Predicate pushdown, projection pushdown, etc.
- **Query Plan** `user-guide/lazy/query-plan.md` - `explain()` and understanding optimization

### IO
- **IO Overview** `user-guide/io/index.md` - Reading and writing data
- **CSV** `user-guide/io/csv.md` - `read_csv`, `scan_csv`, `write_csv`
- **Parquet** `user-guide/io/parquet.md` - `read_parquet`, `scan_parquet`, `write_parquet`
- **JSON** `user-guide/io/json.md` - `read_json`, `read_ndjson`
- **Database** `user-guide/io/database.md` - SQL database connections
- **Cloud Storage** `user-guide/io/cloud-storage.md` - S3, GCS, Azure Blob

### Migration
- **From pandas** `user-guide/migration/pandas.md` - pandas to Polars translation guide
- **From Spark** `user-guide/migration/spark.md` - Spark to Polars translation guide
