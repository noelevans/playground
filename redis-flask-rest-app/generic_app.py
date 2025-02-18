from flask import Flask, jsonify, make_response, request, abort
import json
import redis


app = Flask(__name__)
rdb = redis.StrictRedis(
    db=0,
    encoding='utf-8',
    decode_responses=True)


@app.route('/api/get/<key>', methods=['GET'])
def get(key):
    """
    Generic get, expecting key to be
    user:anna, user:bill, email:clare@gmail.com, email:dan@outlook.com, etc
    """
    response = rdb.get(key)
    if not response:
        return abort(404, '{} not found'.format(key))
    return jsonify(key, json.loads(response))


@app.route('/api/get_all/<entity>', methods=['GET'])
def get_all(entity):
    """
    Get all where entity is either 'user' or 'email'
    """
    keys = rdb.scan_iter('{}:*'.format(entity)) or []
    return jsonify({k: json.loads(rdb.get(k)) for k in keys})


@app.route('/api/create/<key>', methods=['POST'])
def create(key):
    """
    Generic create where key is either
    user:abc or email:f@g.com

    For user:anna, the request json should be like so:
        {
            'email': ['anna@gmail.com', 'anna@aol.com'],
            'first_name': 'Anna',
            'last_name': 'Zander'
        }
    """
    if not request.json:
        abort(400, 'Bad request')
    value = json.dumps({jk: request.json[jk] for jk in request.json.keys()})
    rdb.set(key, value)
    return value, 201


@app.route('/api/delete/<key>', methods=['DELETE'])
def delete_contact(key):
    """
    Generic delete where key can be 'user:abc' or 'email:f@g.com'
    """
    count = rdb.delete(key)
    if not count:
        return make_response(
            jsonify({'error': 'Non-existant key'}), 409)
    return json.dumps({'result': True})


@app.route('/api/update/<key>', methods=['PUT'])
def update(key):
    """
    As with create, this expects a key:
    'user:abc' or 'email:f@g.com'

    For user:anna, the request json should have *some* of these fields
        {
            'email': ['anna@gmail.com', 'anna@aol.com'],
            'first_name': 'Anna',
            'last_name': 'Zander'
        }

    """
    raw_json = rdb.get(key)
    if not raw_json:
        abort(400, 'Bad key')
    old_value = json.loads(raw_json)
    all_keys = set(old_value.keys()).union(set(request.json.keys()))
    value = {
        jk: request.json.get(jk, old_value[jk])
        for jk in all_keys}
    rdb.set(key, json.dumps(value))
    return json.dumps(value)


if __name__ == '__main__':
    app.run(debug=True)
