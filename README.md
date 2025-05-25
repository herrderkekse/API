# Waschbezahlsystem
This project aims to provide a FOSS alternative to expensive, proprietary coin-based payment systems commonly used in washing machines and similar equipment. It is designed to replace traditional physical payment terminals with a flexible, digital solution that allows users to pay for usage time.

That being said, the 'free' part only applies to the software part of the system. You are still gonna need to provide the necessary hardware infrastructure and host it yourself/pay someone to do it. Additionally, for each device, a separate, inexpensive ESP-32 controller is required.

# Quickstart
TDB

# Modules
The system consists of three main modules:
1. Backend: A Python FastAPI + MariaDB solution that handles user authentication, device management, and payment processing. It also includes WebSocket endpoints for real-time device status updates.
2. Frontend: 
   1. Web Interface: A React Web App that provides a user-friendly interface for users to interact with the system from everywhere.
   2. Physical Terminal: (TBD) A physical terminal that can be used to interact with the system. It will probably be a touch screen device with a web browser.
   3. Mobile App (TBD): A mobile app that can be used to interact with the system instead of the browser.
3. Machine Controller: An ESP-32 based controller that interfaces with the washing machine and communicates with the backend via WebSocket.

# Contributions
Contributions are welcome! Please use an existing issue or open a new one to document your progress and create a pull request if you want to contribute. Please create separate pull requests for each issue you're adressing and make sure you follow the coding style and conventions used in the project. You can also open an issue for feature requests or bug reports, but if you want it fast, your best bet is to implement it yourself and open a pull request.

# Disclaimer
You are gonna handle user data, including passwords and payment information. Though this project provides a starting point and a solid foundation, it is ultimately your responsibility to ensure the security of the system. Make sure you know what you are doing and have a good understanding of security best practices before deploying this system. The maintainers of this project are not responsible for any damages caused by the use of this software.