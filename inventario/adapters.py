from allauth.account.adapter import DefaultAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    #esto es para bloquear el registo para gente que se quiere registrar 

    def is_open_for_signup(self, request):
        # asi siemrpe  devuelve False, nadie se puede registrar 
        return False
