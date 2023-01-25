from flask import Flask, jsonify, request
from neo4j import GraphDatabase
import os
import uuid

app = Flask(__name__)

EMPLOYEE = "Employee"
DEPARTMENT = "Department"
WORKS_IN = "WORKS_IN"
MANAGES = "MANAGES"

INITIALISE = False

db = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "test1234"))
if INITIALISE:
    with db.session() as session:
        session.run(f"""CREATE 
        (a:{EMPLOYEE} {{id: "{uuid.uuid4()}", firstName: "Adam", lastName: "Adamski", position: "Reżyser"}}),
        (b:{EMPLOYEE} {{id: "{uuid.uuid4()}", firstName: "Adam", lastName: "Niedamski", position: "Scenarzysta"}}),
        (c:{EMPLOYEE} {{id: "{uuid.uuid4()}", firstName: "Basia", lastName: "Basiarska", position: "Dźwiękowiec"}}),
        (d:{EMPLOYEE} {{id: "{uuid.uuid4()}", firstName: "Cezary", lastName: "Pazura", position: "Aktor"}}),

        (f:{DEPARTMENT} {{id: "{uuid.uuid4()}", name: "Komedia"}}),
        (g:{DEPARTMENT} {{id: "{uuid.uuid4()}", name: "Dramat"}}),
        (h:{DEPARTMENT} {{id: "{uuid.uuid4()}", name: "Akcja"}}),

        (a)-[:{WORKS_IN}]->(f),
        (f)-[:{MANAGES}]->(a),
        (a)-[:{WORKS_IN}]->(g),
        (g)-[:{MANAGES}]->(a),
        (b)-[:{WORKS_IN}]->(h),
        (h)-[:{MANAGES}]->(b),
        (c)-[:{WORKS_IN}]->(h),
        (h)-[:{MANAGES}]->(c),
        (d)-[:{WORKS_IN}]->(f),
        (f)-[:{MANAGES}]->(d)
        """)

driver = GraphDatabase.driver("neo4j://localhost:7687", auth=("neo4j", "test1234"))

@app.route('/employees', methods=['GET'])
def get_employees():
    params = request.args
    sort = params.get("sort")
    filter = params.get("filter")
    filterValue = params.get("filterValue")
    query = f"""
        MATCH (e:Employee {f"{{{filter}: '{filterValue}'}}" if filter and filterValue else ""})
        RETURN e
        {"ORDER BY e." + sort if sort else ""}
        """

    with db.session() as session:
        results = session.run(query)
        mapped_result = list(map(lambda x: x.data()["e"], list(results)))
        return mapped_result

@app.route('/employees', methods=['POST'])
def add_employee():
    firstName = request.json['firstName']
    lastName = request.json['lastName']
    position = request.json['position']
    matchQuery = f"""MATCH (e:Employee {{firstName: "{firstName}", lastName: "{lastName}"}}) RETURN e"""
    addQuery = f"""CREATE (e:Employee {{id: "{uuid.uuid4()}", firstName: "{firstName}", lastName: "{lastName}", position: "{position}"}})"""

    if not firstName or not lastName or not position:
        response = {"message": "Nie podano wszystkich danych"}
        return response

    with driver.session() as session:
        employees = session.run(matchQuery).data()

    for employee in employees:
        if employee['firstName'] == firstName and employee['lastName'] == lastName:
            response = {"message": "Podane imię i nazwisko już istnieje"}
            return response

    with driver.session() as session:
        session.run(addQuery)

    response = {'status': 'success'}
    return response

@app.route("/employees/<string:id>", methods=['PUT'])
def update_employee_route(id):
    firstName = request.json['firstName']
    lastName = request.json['lastName']
    position = request.json['position']
    matchQuery = f"""MATCH (e:Employee) WHERE e.id="{id}" RETURN e"""
    updateQuery = f"""MATCH (e:Employee) WHERE e.id="{id}" SET e.firstName="{firstName}", e.lastName="{lastName}", e.position="{position}\""""

    with driver.session() as session:
        result = session.run(matchQuery).data()
        if not result:
            response = {'message': 'Employee not found'}
            return response, 404
        session.run(updateQuery)
        response = {'status': 'success'}
        return response

@app.route("/employees/<string:id>", methods=['DELETE'])
def delete_employee_route(id):
    query = f"""MATCH (e:Employee) WHERE e.id="{id}" DETACH DELETE e"""

    with driver.session() as session:
        res = session.run(query).data()

    if not res:
        response = {'message': 'Employee not found'}
        return response, 404

    response = {'status': 'success'}
    return response

def find_employee_subordinates(tx, id):
    query = "MATCH (e:Employee) WHERE id(e)=$id RETURN e"
    result = tx.run(query, id=int(id)).data()
    if not result:
        return None
    query = "MATCH (e:Employe)-[:MANAGES]->(sub:Employee) WHERE id(e)=$id RETURN sub"
    results = tx.run(query, id=int(id)).data()
    subordinates = [{'firstName': result['e']['firstName'], 'lastName': result['e']['lastName'],
                     'position': result['e']['position']} for result in results]
    return subordinates

@app.route("/employees/<string:id>/subordinates", methods=["GET"])
def find_employee_subordinates_route(id):
    with driver.session() as session:
        employees = session.read_transaction(find_employee_subordinates, id)

    response = {f'Subordinates of {id}': employees}

    return response

def find_department_by_employee(tx, id):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE id(e)=$id RETURN d"
    results = tx.run(query, id=int(id)).data()
    if not results:
        return None
    department_data = [{'name': result['d']['name'], "Info:": '...'} for result in results]
    return department_data

@app.route("/employees/<string:id>/department", methods=['GET'])
def find_department_by_employee_route(id):
    with driver.session() as session:
        departament = session.read_transaction(find_department_by_employee, id)

    response = {f'departament of {id}': departament}

    return response

@app.route("/departments", methods=['GET'])
def get_departments_route():
    params = request.args
    sort = params.get("sort")
    filter = params.get("filter")
    filterValue = params.get("filterValue")
    query = f"""
        MATCH (d: Department {f"{{{filter}: '{filterValue}'}}" if filter and filterValue else ""})
        RETURN d
        {"ORDER BY d." + sort if sort else ""}
        """

    with db.session() as session:
        results = session.run(query)
        mapped_result = list(map(lambda x: x.data()["d"], list(results)))
        return mapped_result


def find_department_employes(tx, id):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department) WHERE id(d)=$id RETURN e"
    results = tx.run(query, id=int(id)).data()
    if not results:
        return None
    employees = [{'firstName': result['e']['firstName'], 'lastName': result['e']['lastName'],
                  'position': result['e']['position']} for result in results]
    return employees


@app.route("/departments/<string:id>/employees", methods=['GET'])
def get_department_employees(id):
    with driver.session() as session:
        employees = session.read_transaction(find_department_employes, id)

    response = {"employees": employees}
    return response

if __name__ == '__main__':
    app.run()