from query_engine import run_fn, Filter, QueryPlan
from query import ensure_firestore, format_results

'''
test_one ensures that the query "population == 0" returns three towns:
Warner's Grant, Avery's Gore, and Lewis
'''
def test_one():
    db = ensure_firestore()
    filters = [("", Filter(field="population", op="==", value=0))]
    plan = QueryPlan(filters=filters)
    result = run_fn(db, plan)
    for r in result:
        if not (r["town_name"] == "Warner's Grant" or r["town_name"] == "Avery's Gore" or r["town_name"] == "Lewis"):
            print("FAILED TEST ONE")
            return
    print("PASSED TEST ONE")

'''
test_two ensure that the query "population of Cambridge"
returns 3186
'''
def test_two():
    db = ensure_firestore()
    filters = [("", Filter(field="population", op="OF", value="Cambridge"))]
    plan = QueryPlan(filters=filters)
    result = run_fn(db, plan)
    if len(result) == 0:
        print("FAILED TEST TWO - length should be 1, not 0")
        return
    if result[0] == 3186:
        print("PASSED TEST TWO")
        return
    print("FAILED TEST TWO")

'''
test_three ensures that the compound query "population < 200 and county == Essex"
returns Warner's Grange, Avery's Gore, Lewis, Averill, Warren's Gore, Ferdinand
'''
def test_three():
    db = ensure_firestore()
    filters = [("", Filter(field="population", op="<", value=50)),
               ("AND", Filter(field="county", op="==", value="Essex"))]
    plan = QueryPlan(filters=filters)
    result = run_fn(db, plan)
    for r in result:
        if not (r["town_name"] == "Warner's Grant" or r["town_name"] == "Avery's Gore" or
                r["town_name"] == "Lewis" or r["town_name"] == "Averill" or
                r["town_name"] == "Warren's Gore" or r["town_name"] == "Ferdinand"):
            print("FAILED TEST TEST THREE")
            return
    print("PASSED TEST THREE")

'''
test_four checks to make sure that the query "url of "Avery's Gore""
returns "None" since the url does not exist
'''
def test_four():
    db = ensure_firestore()
    filters = [("", Filter(field="url", op="OF", value="Avery's Gore"))]
    plan = QueryPlan(filters=filters)
    result = run_fn(db, plan)
    if format_results(result) == "None":
        print("PASSED TEST FOUR")
        return
    print('FAILED TEST FOUR')

'''
test_five checks to make sure that the query "url of "Buel's Gore""
returns "no information" since the town does not exist
'''
def test_five():
    db = ensure_firestore()
    filters = [("", Filter(field="url", op="OF", value="Buel's Gore"))]
    plan = QueryPlan(filters=filters)
    result = run_fn(db, plan)
    if format_results(result) == 'no information available. To learn more type "help"':
        print("PASSED TEST FIVE")
        return
    print('FAILED TEST FIVE')

if __name__ == "__main__":
    test_one()
    test_two()
    test_three()
    test_four()
    test_five()