SECRETS APP
===========

Secrets App is a simple Flask Demo app.
It provides the following endpoints:


## create users: 

```POST /users```
 and
 ```{"username": "foo_bar@example.com",
 "password": "mysecretpassword"}```

You will receive an email with an authorization url. Only authorized users will be able to log in!

## validate user account
``` GET POST PATCH /users/<int:user_id>/validation/<string:validation_token>```

Validate the email address for a user account. This can be done by a GET, POST or PATCH method. Note that this function is idempotent.

## get users details:

```GET /users/<int:user_id>```

Returns the name and id for a given user id. 
You need to be logged in to see users details.


## create secrets:
```POST /secrets```

```
{"secret": "this is a super secret message"}
```

Create a secret message. Be aware that your username will be linked to this ressource - others will be able to see who created the message. You'll need to be logged in to use this endpoint.


## list all secrets

```GET /secrets```

returns a list of all stored secrets:

```json
{
  "secrets": [
    {
      "created_by": "user@gerneth.info",
      "id": 1,
      "secret": "this is a super secret message"
    },
    {
      "created_by": "testuser@example.com",
      "id": 2,
      "secret": "I like snickers"
    }
  ]
}
```
You'll need to be logged in to use this endpoint.
