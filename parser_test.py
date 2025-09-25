from parser import parse_query
from query_engine import Filter, QueryPlan
'''
Tests for parser.py
'''

# tests for validate(tree)

# tests for _validate_expr()

# tests for _atom_to_dict()

# tests for _validate_atom()

# tests for _first_token()

# tests for _convert_to_query_plan()

# tests for parse_query()
'''
test_one ensures that multi-word tokens require quotation marks
'''
def test_parse_query_one():
    query = "county == grand isle"
    if "Invalid query: Incomplete query. " in parse_query(query):
        print("PASSED TEST ONE: parse_query multi-word tokens require quotes")
        return
    print("FAILED TEST ONE: parse_query multi-word tokens require quotes")
'''
test two ensure that parse_query ignores whitespace
'''
def test_parse_query_two():
    query = "       population     >       5000"
    filters = Filter("population", ">", 5000)
    query_plan = QueryPlan(filters=[("", filters)])
    if parse_query(query) == query_plan:
        print("PASSED TEST TWO: parse_query(), ignore whitespace")
        return
    print("FAILED TEST TWO: parse_query(), ignore whitespace")

'''
tests to ensure that only on compound operator (AND/OR) is allowed at once
'''
def test_parse_query_three():
    query = "population < 10 AND altitude > 500 and county == Lamoille"
    if parse_query(query) == "Invalid query: Cannot use more than one AND/OR operator":
        print ("PASSED TEST THREE: parse_query(), multiple compound operators")
        return
    print("FAILED TEST THREE: parse_query(), multiple compound operators")
'''
tests to ensure that parse_query does not allow OF operator to be used with compound operators
'''
def test_parse_query_four():
    of_and_query = "population of Cambridge and county == Lamoille"
    of_or_query = "population of Cambridge or county == Lamoille"
    if parse_query(of_and_query) == "Invalid query: Cannot use AND/OR with OF operator. Use OF queries separately or combine OF with regular comparisons." \
        and parse_query(of_or_query) == "Invalid query: Cannot use AND/OR with OF operator. Use OF queries separately or combine OF with regular comparisons.":
        print("PASSED TEST FOUR: parse_query(), OF with compound operator")
        return
    print("FAILED TEST FOUR: parse_query(), OF with compound operator")
'''
tests to ensure that unknown fields are not allowed
'''
def test_parse_query_five():
    query = "popcorn < 500"
    if parse_query(query) == "Invalid query: Unknown field 'popcorn'":
        print("PASSED TEST FIVE: parse_query(), unknown field")
        return
    print("FAILED TEST FIVE: parse_query(), unknown field")
'''
tests to ensure that double operators aren't allowed
'''
def test_parse_query_six():
    and_and_query = "population < 500 and and altitude > 500"
    or_or_query = "population < 500 or or altitude > 500"
    if parse_query(and_and_query) == "Invalid query: Double operator detected. Use only one AND or OR between conditions." \
        and parse_query(or_or_query) == "Invalid query: Double operator detected. Use only one AND or OR between conditions.":
        print("PASSED TEST SIX: parse_query(), double compound operators")
        return
    print("FAILED TEST SIX: parse_query(), double compound operators")

'''
tests to make sure that no incomplete compound queries permitted
'''
def test_parse_query_seven():
    incomplete_query = "population < 500 and "
    if parse_query(incomplete_query) == "Invalid query: Incomplete compound query. Missing condition after AND/OR operator.":
        print("PASSED TEST SEVEN: parse_query(), incomplete compound query")
        return
    print("FAILED TEST SEVEN: parse_query(), incomplete compound query")

'''
test 8 ensures that incomplete queries aren't permitted
'''
def test_parse_query_eight():
    incomplete_query = "population <"
    result = parse_query(incomplete_query)
    if isinstance(result, str) and result.startswith("Invalid query: Expected"):
        print("PASSED TEST EIGHT: parse_query(), incomplete query")
        return
    print("FAILED TEST EIGHT: parse_query(), incomplete query")

if __name__ == '__main__':
    test_parse_query_one()
    test_parse_query_two()
    test_parse_query_three()
    test_parse_query_four()
    test_parse_query_five()
    test_parse_query_six()
    test_parse_query_seven()
    test_parse_query_eight()
