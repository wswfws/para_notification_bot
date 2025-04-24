module.exports = {
  apps: [
    {
      name: "telegram-bot",
      script: "/usr/bin/python3",  // полный путь
      args: "./main.py",           // относительный или полный путь
      interpreter: "none",         // отключите интерпретатор PM2 для Python
      watch: true,
      max_restarts: 10,
      env: {
        NODE_ENV: "development",
        PYTHONIOENCODING: "utf-8"  // явно задаём кодировку
      }
    }
  ]
};