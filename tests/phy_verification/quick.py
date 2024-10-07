import ble_test_suite.phy.rx_sensitivity as rx_sens
from ble_test_suite.controllers import RxSensitivityTestController


cfg = rx_sens.init_from_json('phyTest_master.json')
ctrl = RxSensitivityTestController(cfg)

ctrl.run_test()
ctrl.results()