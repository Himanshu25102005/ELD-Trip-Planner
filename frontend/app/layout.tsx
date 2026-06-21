import "./globals.css";

export const metadata = {
  title: "ELD Trip Planner",
  description: "FMCSA-compliant trucking trip planner and daily log generator",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
