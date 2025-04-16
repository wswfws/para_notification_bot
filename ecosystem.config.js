module.exports = {
  apps: [
    {
      name: "telegram-bot",
      script: "python3",
      args: "main.py",
      interpreter: "python3",
      watch: true,
      env: {
        NODE_ENV: "development",
      },
    },
  ],
};