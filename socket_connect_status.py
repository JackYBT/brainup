class SocketConnectStatus:
    def __init__(self, status):
        self.connect = status
        self.ble_is_alive = True


class FilterParams:
    def __init__(self, filter_param,draw_number,if_save_data=False,save_action=False,save_type=1,notch_filter=1):
        self.filter_param = filter_param
        self.draw_number=draw_number
        self.if_save_data=if_save_data
        self.save_action=save_action
        self.save_type=save_type
        self.notch_filter=notch_filter

