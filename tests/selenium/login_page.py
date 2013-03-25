import ConfigParser
import page


class LoginPage(page.Page):

    def login(self):
        config = ConfigParser.RawConfigParser()
        config.read('conf.ini')
        url = config.get('server', 'address')
        user = config.get('server', 'user')
        password = config.get('server', 'password')

        self.Open(url)

        self.EditBox('username').Set(user)
        self.EditBox('password').Set(password)
        xpath = "//button[@type='submit']"
        self.Button(xpath).Click()

        return self
