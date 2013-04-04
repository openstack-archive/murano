import page


class ServicesDetailsPage(page.Page):
    
    name = 'ServicesDetails'

    def get_service_name(self):
        self.Refresh()
        self.Link('Service').Click()
        return self.TableCell('Name').Text()

    def get_service_domain(self):
        self.Refresh()
        self.Link('Service').Click()
        return self.TableCell('Domain').Text()