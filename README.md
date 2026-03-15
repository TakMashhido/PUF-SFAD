# PUF SFAD Simulation

This repository contains the simulation code and formal proofs for PUF-SFAD, a Physical Unclonable Function (PUF) based Secure Firmware Update scheme.

## Project Structure

- `code/`: Contains the simulation source code, including the server application, device simulator, PUF implementation, and cryptographic protocols.
  - `src/puf.py`: Simulation of the SRAM PUF.
  - `src/server_app.py`: Flask-based provisioning server providing the web UI and update APIs.
  - `src/device_app.py`: Simulated device logic.
  - `src/protocols.py`: Cryptographic protocols used in the scheme.
  - `src/legitimate_simulator.py`: Orchestrates the simulation between server and devices, tracking the lifecycle of simulated devices.
- `formal proof/`: Contains the Tamarin prover script (`PUF_SFAD.spthy`) for the formal verification of the protocol.
- `docker-compose.yml`: Configuration for running the simulation environment using Docker.

## Running the Simulation

The project is containerized using Docker, allowing you to easily run the server and simulated devices.

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) installed.
- [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Start the Simulation
1. Clone the repository and navigate to the project directory:
   ```bash
   git clone https://github.com/TakMashhido/PUF-SFAD.git
   cd PUF-SFAD
   ```
2. Start the Docker containers:
   ```bash
   docker-compose up --build
   ```
   This will start both the provisioning server (`puf_server`) and the device simulator (`puf_legitimate_sim`). The simulator automatically starts one device upon initialization.

### Interacting with the Simulation
The provisioning server provides a web dashboard and APIs for managing the devices.

1. **Open the Dashboard**:
   Open a web browser and navigate to `http://localhost:5000`. Here you can view live events and device statistics.
2. **Add More Devices**:
   You can instantiate additional simulated devices by sending a POST request to the server:
   ```bash
   curl -X POST http://localhost:5000/api/control/create_device
   ```
3. **Trigger Firmware Updates**:
   You can manually trigger a firmware update for a specific enrolled device. First, find the `device_id` (from the dashboard or logs), and then send a POST request:
   ```bash
   curl -X POST http://localhost:5000/api/control/trigger_update -H "Content-Type: application/json" -d '{"device_id": "YOUR_DEVICE_ID"}'
   ```
4. **View Logs**:
   The dashboard at `http://localhost:5000` will stream the progress as devices retrieve firmware, unpack it utilizing their simulated SRAM PUF, and verify the tags.

## Formal Verification

The protocol's security properties have been formally verified using the [Tamarin Prover](https://tamarin-prover.com/). The proof script is located in `formal proof/PUF_SFAD.spthy`. The formal proof proves the confidentiality, device-firmware binding, origin authentication, and unclonability properties. To test it, install Tamarin and run:

```bash
tamarin-prover --prove formal\ proof/PUF_SFAD.spthy
```
