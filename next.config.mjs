/** @type {import('next').NextConfig} */
const nextConfig = {
    reactStrictMode: true,

    // Production API URL configuration
    async rewrites() {
        // Use environment variable for production, fallback to localhost for dev
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5001';

        return [
            {
                source: '/api/:path*',
                destination: `${apiUrl}/api/:path*`,
            },
        ];
    },
};

export default nextConfig;
