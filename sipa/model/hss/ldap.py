import ldap3

from flask import current_app


def get_ldap_connection(user, password, use_ssl=True):
    """Test method to establish an ldap connection"""
    host = current_app.config['HSS_LDAP_HOST']
    port = current_app.config['HSS_LDAP_PORT']
    server = ldap3.Server(host, port, use_ssl=use_ssl,
                          get_info=ldap3.GET_ALL_INFO)
    userdn_format = current_app.config['HSS_LDAP_USERDN_FORMAT']

    user_dn = (user if "dc=wh12,dc=tu-dresden,dc=de" in user
               else userdn_format.format(user=user))

    return ldap3.Connection(server, auto_bind=True,
                            client_strategy=ldap3.STRATEGY_SYNC,
                            user=user_dn, password=password,
                            authentication=ldap3.AUTH_SIMPLE)
