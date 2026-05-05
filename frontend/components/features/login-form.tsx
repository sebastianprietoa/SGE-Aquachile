"use client";

import type { FormEvent } from "react";
import { useState } from "react";

import { api } from "@/lib/api";
import { setStoredToken } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginForm() {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("Admin1234!");
  const [message, setMessage] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const response = await api.login({ username, password });
      setStoredToken(response.access_token);
      setMessage(`Sesión iniciada como ${response.user.username}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No fue posible autenticar");
    }
  }

  return (
    <Card className="max-w-md">
      <CardHeader>
        <CardTitle>Acceso inicial</CardTitle>
        <CardDescription>Login simple con usuario seed para operar el MVP.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="username">Usuario</Label>
            <Input id="username" value={username} onChange={(event) => setUsername(event.target.value)} />
          </div>
          <div>
            <Label htmlFor="password">Contraseña</Label>
            <Input id="password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </div>
          <Button type="submit" className="w-full">
            Ingresar
          </Button>
          {message ? <p className="text-sm text-slate-300">{message}</p> : null}
        </form>
      </CardContent>
    </Card>
  );
}
