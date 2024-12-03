# Eris 2.0

A Discord bot that streamlines flag submission and approval in your server! 🎌

With this bot, members can submit flags for review, and admins can approve or reject them with ease.

## 🛠️ **Features**

- **Flag Submission**: Members can submit flags using simple commands.
- **Admin Moderation**: Admins can approve or reject submitted flags directly in Discord.
- **Notification System**: Submitters are notified of their flag’s status.
- **Customizable Settings**: Adjust roles, submission channels, and more.
- **Maintain Leaderboards**: Maintain a leaderboard powered by MongoDB.
- **Dockerized**: Use Docker Compose for easy deployment and scaling.


## 🚀 Getting Started  

### Prerequisites  
- Python 3.9+  
- Docker & Docker Compose installed on your machine  
- A Discord bot token (available from the [Discord Developer Portal](https://discord.com/developers/applications))  

### 1. Clone the Repository  
```bash  
git clone https://github.com/yourusername/flag-submission-bot.git  
cd flag-submission-bot  
```  

### 2. Set Up Environment Variables  
Modify the `config.py` accordingly:  
```config.py  
DISCORD_TOKEN=your-discord-bot-token  
MONGO_URI=mongodb://mongo:27017/flagdb  
PREFIX=!  
```  

### 3. Run with Docker Compose  
Build and start the bot along with its MongoDB instance using Docker Compose:  
```bash  
docker-compose up --build  
```  
!(hi)[https://github.com/Cypher042/Eris2.0/blob/main/Screenshot%202024-12-03%20125605.png?raw=true]
