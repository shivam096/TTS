class Validator:
    def validate(self, sql_query):
        # Basic validation (no DELETE without WHERE)
        if 'DELETE' in sql_query.upper() and 'WHERE' not in sql_query.upper():
            print("Invalid SQL detected!")
            return False
        return True