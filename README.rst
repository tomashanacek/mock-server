Mock server
===========

Simple mock server for REST and XML-RPC API

It can mock GET, POST, PUT, PATCH, DELETE and some more rarely used HTTP methods.

Build status at `Travis CI <http://travis-ci.org/>`_: |travis|

.. |travis| image:: https://travis-ci.org/tomashanacek/mock-server.png?branch=master
    :target: https://travis-ci.org/tomashanacek/mock-server

DEMO
====

http://demo.mockapi.org/__manage

Installation
============

Install with pip::

    $ pip install mock-server


Or install with easy_install::

    $ easy_install mock-server

And after run::

    $ mock-server --dir=/path/to/api

It will be listening on port 8888 and wait for your HTTP requests.

Overview
========

| For create mock for url path go to:
|
| http://localhost:8888/__manage/create
|

Mocked GET /user/tom::

    $ curl -v -X GET http://demo.mockapi.org/user/tom

    > GET /user/tom HTTP/1.1
    > Host: demo.mockapi.org
    > Accept: */*
    >
    < HTTP/1.1 200 OK
    < Access-Control-Allow-Origin: *
    < Content-Type: application/json; charset=utf-8
    < Content-Length: 64
    < Server: TornadoServer/2.4.1
    <
    {
        "name": "Tom",
        "surname": "Smith",
        "age": 22
    }

Features
========
- Mocking REST API.
- Mocking RPC API (xml, json).
- Upstream server proxy (proxy an existing api).
- Variables in url path.
- Simple api documentation (markdown).
- Api authentication (HTTP Basic authentication).


Format
======

response content format: ``%METHOD%_%STATUS%.%FORMAT%``

response headers format: ``%METHOD%_H_%STATUS%.%FORMAT%``

::

    root_dir/
        GET_200.json         # response content for GET /
        GET_H_200.json       # headers for GET /
        user/
            DELETE_404.xml   # response content for DELETE /user.xml?__statusCode=404
            POST_200.json    # response content for POST /user
            POST_H_200.json  # headers for POST /user


Bug report
==========

If you have any trouble, report bug at GitHub Issue https://github.com/tomashanacek/mock-server/issues

Contributors
============
William Zhang
