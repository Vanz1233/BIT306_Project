class RequestLogMiddleware:
    """
    Rubric 2.4 & 3.4: Middleware to handle cross-cutting concerns (Logging).
    Demonstrates Inversion of Control (IoC) by intercepting the request lifecycle.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Logic BEFORE the view is called (Pre-processing)
        print(f"------------")
        print(f"[Middleware] Incoming Request: {request.method} {request.path}")
        print(f"[Middleware] User: {request.user}")

        # 2. Pass control to the next layer (Django controls the flow)
        response = self.get_response(request)

        # 3. Logic AFTER the view is called (Post-processing)
        print(f"[Middleware] Response Status: {response.status_code}")
        print(f"------------")
        
        return response