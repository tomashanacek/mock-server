## Mock Server
Simple mock server for REST and XML-RPC API

It can mock GET, POST, PUT, PATCH, DELETE and some more rarely used HTTP methods. 

Build status at [Travis CI](http://travis-ci.org/): [![Build Status](https://travis-ci.org/tomashanacek/mock-server.png?branch=master)](https://travis-ci.org/tomashanacek/mock-server)

## DEMO

http://psyduck.cz:9999/__manage

## Installation

Install with pip:

    $ pip install mock-server

Or install with easy_install

    $ easy_install mock-server

And after run

    $ mock-server --dir=/path/to/api
    
It will be listening on port 8888 and wait for your HTTP requests.

## Overview

Mocking service is as simple as creating directory and few files within it just like that:

    response content format: %METHOD%_%STATUS%.%FORMAT%
    response headers format: %METHOD%_H_%STATUS%.%FORMAT%

    root_dir/
        GET_200.json         # response content for GET /
        GET_H_200.json       # headers for GET /
        user/
            DELETE_404.xml   # response content for DELETE /user.xml?__statusCode=404
            POST_200.json    # response content for POST /user
            POST_H_200.json  # headers for POST /user
            

Or you can use web interface

    http://localhost:8888/__manage/create


Mocked GET /user/tom 

    $ curl -v -X GET http://psyduck:9999/user/tom
    
    > GET /user/tom HTTP/1.1
    > Host: psyduck:9999
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


## Bug report
If you have any trouble, report bug at GitHub Issue https://github.com/tomashanacek/mock-server/issues
