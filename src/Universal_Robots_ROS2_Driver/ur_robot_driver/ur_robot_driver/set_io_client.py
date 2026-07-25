import rclpy
from rclpy.node import Node
from ur_msgs.srv import SetIO

class SetIOClient(Node):
   def __init__(self):
       super().__init__('set_io_client')
       self.client = self.create_client(SetIO, '/io_and_status_controller/set_io')
       while not self.client.wait_for_service(timeout_sec=1.0):
           self.get_logger().info('서비스를 기다리는 중입니다...')
   def send_request(self, state):
       request = SetIO.Request()
       request.fun = 1              
       request.pin = 0      
       request.state = float(state)   
       future = self.client.call_async(request)
       future.add_done_callback(self.callback)
   def callback(self, future):
       try:
           response = future.result()
           self.get_logger().info(f'Response: {response}')
       except Exception as e:
           self.get_logger().error(f'Service call failed: {e}')
def main(args=None):
   rclpy.init(args=args)
   client = SetIOClient()
   try:
       while(1):
           user_input = int(input("0을 입력하면 출력 HIGH, 1을 입력하면 출력 LOW: "))
           if user_input == 0:
               client.send_request(1)  # HIGH (1)
           elif user_input == 1:
               client.send_request(0)  # LOW (0)
           else:
               print("잘못된 입력입니다. 0 또는 1을 입력하세요.")
   except ValueError:
       print("정수를 입력하세요.")

   rclpy.spin_once(client)  
   client.destroy_node()
   rclpy.shutdown()

if __name__ == '__main__':
   main()
