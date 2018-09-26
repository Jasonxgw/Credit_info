def login(self):
    url = 'https://www.51jt.com/api.jsp'
    data = {"args": ["18645145512", "df4c77661c31b283f1033c4e3bd53683", "1"],
            "argsclass": ["java.lang.String", "java.lang.String", "java.lang.String"],
            "methodName": "userLoginGetUserInfo",
            "proxy": "UserManager"}
    response = self.session.post(url=url, data="json=" + json.dumps(data), verify=False, headers=self.session.headers)
    return response
