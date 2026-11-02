import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./index.css";
import "./App.css";
import "./styles/design-system.css";
import "./styles/landing.css";
import "./styles/register.css";
import "./styles/login.css";
import "./styles/community.css";
import "./styles/mentors.css";
import "./styles/content.css";
import "./styles/chats.css";
import "./styles/dashboard.css";
import "./styles/admin.css";
import "./styles/vibrance.css";
import "./styles/dark.css";
import { ClerkProvider } from "@clerk/react";

const publishableKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
const root = <App />;

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    {publishableKey ? <ClerkProvider publishableKey={publishableKey}>{root}</ClerkProvider> : root}
  </React.StrictMode>
);
