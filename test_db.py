from app.db import get_schema

from app.db import get_foreign_keys

schema = get_schema()

for table, columns in schema.items():
    print(f"\n{table}")

    for column in columns:
        print(
            f"  {column['name']} "
            f"({column['type']}) "
            f"{column['key']}"
        )




foreign_keys = get_foreign_keys()

for fk in foreign_keys:
    print(
        f"{fk['TABLE_NAME']}.{fk['COLUMN_NAME']} "
        f"-> "
        f"{fk['REFERENCED_TABLE_NAME']}."
        f"{fk['REFERENCED_COLUMN_NAME']}"
    )