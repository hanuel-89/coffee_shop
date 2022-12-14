import json
from flask import request, _request_ctx_stack, abort
from functools import wraps
from jose import jwt
from urllib.request import urlopen


AUTH0_DOMAIN = 'digital-coffee-shop.us.auth0.com'
ALGORITHMS = ['RS256']
API_AUDIENCE = 'coffee'

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Header

'''
@TODO implement get_token_auth_header() method
    it should attempt to get the header from the request
        it should raise an AuthError if no header is present
    it should attempt to split bearer and the token
        it should raise an AuthError if the header is malformed
    return the token part of the header
'''
def get_token_auth_header():
    """This method gets the access token from the Authorization header
    if it is available.
    Args:
        None
    Returns:
        splits[1]: The bearer token generate by Auth0
    Raises:
        AuthError if authorization fails
    """
    try:
        auth = request.headers['Authorization']
    except Exception:
        abort(401)
    if not auth:
        raise AuthError({
            'code': 'authorization header is missing',
            'description': 'Authorization header is required'
        }, 401)

    splits = auth.split()
    if splits[0].lower() != 'bearer':
        raise AuthError({
            'code': 'invalid header',
            'description': 'Authorization header must start with keyword "Bearer".'
        }, 401)

    elif len(splits) == 1:
        raise AuthError({
            'code': 'invalid header',
            'description': 'Token not found.'
        }, 401)

    elif len(splits) > 2:
        raise AuthError({
            'code': 'invalid header',
            'description': 'Authorization header must be bearer token.'
        }, 401)

    return splits[1]

'''
@TODO implement check_permissions(permission, payload) method
    @INPUTS
        permission: string permission (i.e. 'post:drink')
        payload: decoded jwt payload

    it should raise an AuthError if permissions are not included in the payload
        !!NOTE check your RBAC settings in Auth0
    it should raise an AuthError if the requested permission string is not in the payload permissions array
    return true otherwise
'''
def check_permissions(permission, payload):
    """This method checks whether a user has the permission to
    access an endpoint
    Args:
        permission (string): The authorization permission for the endpoint
        payload (json): The decoded JWT paylod
    Returns:
        Boolean: True or False
    Raises:
        AuthError if permissions not in payload
    """
    if 'permissions' not in payload:
        raise AuthError({
            'code': 'Invalid claims',
            'description': 'Permission not included in JWT'
        }, 400)
    elif permission not in payload['permissions']:
        raise AuthError({
            'code': 'unauthorized',
            'description': 'permission not found'
        }, 403)
    else:
        return True

'''
@TODO implement verify_decode_jwt(token) method
    @INPUTS
        token: a json web token (string)

    it should be an Auth0 token with key id (kid)
    it should verify the token using Auth0 /.well-known/jwks.json
    it should decode the payload from the token
    it should validate the claims
    return the decoded payload

    !!NOTE urlopen has a common certificate error described here: https://stackoverflow.com/questions/50236117/scraping-ssl-certificate-verify-failed-error-for-http-en-wikipedia-org
'''
def verify_decode_jwt(token):
    """This method verifies and decodes the JWT
    Args:
        token(json): The bearer token
    Returns:
        decoded_payload(json): The decoded payload
    """
    json_url = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(json_url.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid header',
            'description': 'Malformed authorization'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            return jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer=f'https://{AUTH0_DOMAIN}/')

        except jwt.ExpiredSignatureError as e:
            raise AuthError({'code': 'token_expired', 'description': 'Token expired.'}, 401) from e

        except jwt.JWTClaimsError as e:
            raise AuthError({'code': 'invalid_claims', 'description': 'Incorrect claims. Please, check the audience and issuer.'}, 401) from e

        except Exception as e:
            raise AuthError({'code': 'invalid_header', 'description': 'Unable to parse authentication token.'}, 400) from e

    raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)

'''
@TODO implement @requires_auth(permission) decorator method
    @INPUTS
        permission: string permission (i.e. 'post:drink')

    it should use the get_token_auth_header method to get the token
    it should use the verify_decode_jwt method to decode the jwt
    it should use the check_permissions method validate claims and check the requested permission
    return the decorator which passes the decoded payload to the decorated method
'''
def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                token = get_token_auth_header()
            except Exception:
                abort(401)
            try:
                payload = verify_decode_jwt(token)
            except Exception:
                abort(403)
            try:
                check_permissions(permission, payload)
            except Exception:
                abort(403)
            return f(*args, **kwargs)

        return wrapper
    return requires_auth_decorator