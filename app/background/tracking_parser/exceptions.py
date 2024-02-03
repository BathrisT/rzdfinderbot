class TrackingFinishedException(Exception):
    """Исключение вызывается при попытке обработать трекинг, который был завершен"""

    def __init__(self, tracking_id: int):
        self.tracking_id = tracking_id
