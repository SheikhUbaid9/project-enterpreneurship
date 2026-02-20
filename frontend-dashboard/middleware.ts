import { NextResponse, type NextRequest } from "next/server";

const protectedPaths = ["/inbox", "/thread", "/platforms", "/settings"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("access_token")?.value;
  const pathname = request.nextUrl.pathname;
  const isProtected = protectedPaths.some((path) => pathname.startsWith(path));

  if (isProtected && !token) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname.startsWith("/login") && token) {
    const inboxUrl = new URL("/inbox", request.url);
    return NextResponse.redirect(inboxUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/inbox/:path*", "/thread/:path*", "/platforms/:path*", "/settings/:path*"],
};
