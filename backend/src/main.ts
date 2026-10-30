import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

const PORT = 3001;

async function bootstrap(): Promise<void> {
  // abortOnError: false -> init errors reach the catch below instead of killing the process silently
  const app = await NestFactory.create(AppModule, { abortOnError: false });
  app.setGlobalPrefix('api');
  await app.listen(PORT);
  console.log(`Backend POS demo đang chạy tại http://localhost:${PORT}/api`);
}

bootstrap().catch((error: unknown) => {
  // e.g. missing SQLite file -> show the Vietnamese hint instead of a raw stack trace
  console.error('Không khởi động được backend:', error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
