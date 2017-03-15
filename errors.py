errors = {
	'ParameterException': {
		'message': "Wrong parameter provided",
		'status': 400,
		'extra' : "please provide valid arguments"
	},
	'RessourceExistsException': {
		'message': "A resource with this name already exists",
		'status': 409,
		'extra' : "choose a different resource name"
	},
	'NotFoundException': {
		'message': "This resource does not exist",
		'status': 404,
		'extra': "I am very, very sorry..."
	},
	'ValueError': {
		'message': "Wrong values provided in request",
		'status': 400,
		'extra': "check your parameters and try again"
	}
}


class ParameterException(ValueError):
	pass

class RessourceExistsException(ValueError):
	pass

class NotFoundException(ValueError):
	pass