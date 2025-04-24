module.exports = {
  apps: [
    {
      name: "telegram-bot",
      script: "python3",
      args: "main.py",
      interpreter: "python3",
      watch: true,
      max_restarts: 10, // Добавлено max_restarts
      env: {
        NODE_ENV: "development",
      },
    },
  ],
};
