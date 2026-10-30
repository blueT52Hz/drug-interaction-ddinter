import { BadRequestException, Body, Controller, HttpCode, Post } from '@nestjs/common';
import { InteractionPair } from './interaction-pair.types';
import { InteractionsService } from './interactions.service';

const MAX_CART_DRUGS = 100;

function isValidRegistrationList(value: unknown): value is string[] {
  return (
    Array.isArray(value) &&
    value.length <= MAX_CART_DRUGS &&
    value.every((v) => typeof v === 'string' && v.trim() !== '')
  );
}

@Controller('interactions')
export class InteractionsController {
  constructor(private readonly interactionsService: InteractionsService) {}

  /** POST /api/interactions/check  body: { registrationNumbers: string[] } */
  @Post('check')
  @HttpCode(200)
  check(@Body() body: unknown): { pairs: InteractionPair[] } {
    const registrationNumbers = (body as { registrationNumbers?: unknown } | null)?.registrationNumbers;
    if (!isValidRegistrationList(registrationNumbers)) {
      throw new BadRequestException(`registrationNumbers phải là mảng chuỗi (tối đa ${MAX_CART_DRUGS})`);
    }
    return { pairs: this.interactionsService.check(registrationNumbers) };
  }
}
