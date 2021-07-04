import math

from flask import Flask

from flask_module_mapper import ModuleMapper

import test1
import test2


app = Flask(__name__)

if __name__ == '__main__':
    w = ModuleMapper(app)

    # Testing same modules in different files
    w.map(math)

    # Testing custom modules
    w.map(test1)
    w.map(test2)

    app.run()
