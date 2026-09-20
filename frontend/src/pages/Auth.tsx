import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen } from "lucide-react";
import "./Auth.css";

import { login, signup,  } from "../api.ts";
import { setSession } from "../utils.ts";

export default function Auth() {
  const [isLogin, setIsLogin] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isLogin) {
        try {
            const tokenResult = await login(email, password);
            setSession(tokenResult);
            localStorage.setItem("authenticated", "true");
            navigate("/chat");
        } catch (err) {
            console.error(err);
            alert("Login failed. Please check your credentials.");
        }
    } else {
        try {
            const tokenResult = await signup(email, password);
            setSession(tokenResult);
            localStorage.setItem("authenticated", "true");
            navigate("/chat");
        } catch (err) {
            console.error(err);
            alert("Signup failed. Please try again.");
        }
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-container">

        {/* Left section */}
        <div className="auth-brand">
          <div className="brand-logo">
            <BookOpen size={20} strokeWidth={2.5} />
          </div>

          <span className="brand-name">Granthbodh</span>

          <div className="brand-content">
            <h1>
              Your library, made
              <br />
              conversational.
            </h1>

            <p>
              Sign in to continue exploring
              <br />
              your sources with Granthbodh.
            </p>
          </div>

          <div className="brand-footer">
            Private by design · Your sources stay yours
          </div>
        </div>

        {/* Right section */}
        <div className="auth-form-section">
          <div className="auth-form-container">

            <div className="form-heading">
              <h2>
                {isLogin ? "Welcome back" : "Create your account"}
              </h2>

              <p>
                {isLogin
                  ? "Sign in to continue to your knowledge."
                  : "Start a focused place for your knowledge."}
              </p>
            </div>

            <form onSubmit={handleSubmit}>

              <div className="form-field">
                <label htmlFor="email">
                  Email address
                </label>

                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>

              <div className="form-field">
                <label htmlFor="password">
                  Password
                </label>

                <input
                  id="password"
                  type="password"
                  placeholder="At least 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  minLength={8}
                  required
                />
              </div>

              <button
                type="submit"
                className="submit-button"
              >
                {isLogin ? "Sign in" : "Create account"}
              </button>
            </form>

            <button
              type="button"
              className="auth-switch"
              onClick={() => setIsLogin((prev) => !prev)}
            >
              {isLogin
                ? "Don't have an account? Sign up"
                : "Already have an account? Sign in"}
            </button>

          </div>
        </div>

      </div>
    </div>
  );
}