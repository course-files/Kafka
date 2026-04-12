Run:

```bash
cd microservices_demo/
pip install -r requirements.txt
```

Run the consumers before the producer

```bash
cd microservices_demo/
python consumer_order_notification.py
python consumer_order_inventory.py

python producer_order.py
```

