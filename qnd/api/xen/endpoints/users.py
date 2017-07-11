from flask import request
from flask_restplus import Resource

#from api.xen.business import create_user, delete_user, update_user
from api.xen.serializers import user
from api.restplus import api

from database.models import User
from database import db

import logging.config
log = logging.getLogger(__name__)

ns = api.namespace('xen/users', description='Operations related to users')

@ns.route('/currentuser')
class UserCollection(Resource):

    @api.marshal_list_with(user)
    def get(self):
        """
        Returns the active user.
        """
        obj = type('',(object,),{"name": "Administrator", 
                                 "id": 0,   
                                })()

        return obj

    
