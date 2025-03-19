from rest_framework_simplejwt.authentication import JWTAuthentication

from merchant.models import Merchant

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        header = self.get_header(request)
        if header is None:
            return None

        if isinstance(header, bytes):
            header = header.decode('utf-8')

        if not header.startswith('Bearer '):
            raw_token = header
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception:
            
            try:
                merchant = Merchant.objects.get(hash_api_key=raw_token)
                request.user = merchant.user_account
                return (request.user, raw_token)
            except:
                return None

        return self.get_user(validated_token), validated_token

    def get_raw_token(self, header):
        """
        Extracts the raw token from the header. Supports tokens without 'Bearer'.
        """
        if header.startswith('Bearer '):
            return header.split(' ')[1] 
        return header
