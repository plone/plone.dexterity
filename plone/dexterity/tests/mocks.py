import mocker
import zope.component.testing

class MockTestCase(mocker.MockerTestCase):
    
    def tearDown(self):
        super(MockTestCase, self).tearDown()
        zope.component.testing.tearDown(self)