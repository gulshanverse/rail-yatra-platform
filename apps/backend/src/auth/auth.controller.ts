import {
  Body,
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Post,
  Req,
  Res,
  UseGuards,
} from '@nestjs/common';
import * as express from 'express';
import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { JwtAuthGuard } from './jwt-auth.guard';

@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  @HttpCode(HttpStatus.CREATED)
  async register(@Body() dto: RegisterDto) {
    const user = await this.authService.register(dto);
    return {
      success: true,
      message: 'User registered successfully.',
      data: user,
    };
  }

  @Post('login')
  @HttpCode(HttpStatus.OK)
  async login(
    @Body() dto: LoginDto,
    @Res({ passthrough: true }) response: express.Response,
  ) {
    const result = await this.authService.login(dto);

    // Set refresh token in HttpOnly SameSite Secure cookie
    response.cookie('refresh_token', result.refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
    });

    return {
      success: true,
      message: 'User logged in successfully.',
      data: {
        accessToken: result.accessToken,
        user: result.user,
      },
    };
  }

  @Post('refresh')
  @HttpCode(HttpStatus.OK)
  async refresh(
    @Req() request: express.Request,
    @Res({ passthrough: true }) response: express.Response,
  ) {
    const cookies = request.cookies as
      Record<string, string | undefined> | undefined;
    const refreshToken = cookies?.['refresh_token'];
    if (!refreshToken) {
      return response.status(HttpStatus.UNAUTHORIZED).json({
        success: false,
        error: {
          code: 'REFRESH_TOKEN_MISSING',
          message: 'Refresh token cookie is missing.',
        },
      });
    }

    const payload = this.authService.verifyRefreshToken(refreshToken);
    const accessToken = await this.authService.generateAccessTokenFromUserId(
      payload.sub,
    );

    return {
      success: true,
      data: {
        accessToken,
      },
    };
  }

  @Post('logout')
  @HttpCode(HttpStatus.OK)
  logout(@Res({ passthrough: true }) response: express.Response) {
    response.clearCookie('refresh_token', {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
    });
    return {
      success: true,
      message: 'User logged out successfully.',
    };
  }

  @UseGuards(JwtAuthGuard)
  @Get('me')
  getMe(@Req() request: import('../common/interfaces').AuthenticatedRequest) {
    return {
      success: true,
      data: request.user,
    };
  }
}
