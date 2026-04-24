from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

class VerifyUserView(APIView):
    """
    Acts as a security guard. Takes a username and password, 
    checks the database, and returns the user data if correct.
    """
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Django's built-in password checker
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Send the flat data back to the Gateway!
            return Response({
                'id': user.id, 
                'username': user.username, 
                'is_staff': user.is_staff, 
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

def api_users_list(request):
    """Packages all users into a JSON list for other microservices to read."""
    User = get_user_model()
    
    # Grab all active users and just the fields we are safe to share
    users = User.objects.filter(is_active=True).values(
        'id', 
        'username', 
        'first_name', 
        'last_name', 
        'email', 
        'is_staff'
    )
    
    return JsonResponse(list(users), safe=False)
