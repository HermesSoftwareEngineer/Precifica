# Guia de Autenticação (Frontend)

Este documento descreve como implementar a autenticação no frontend para se comunicar com a API do Precifica.

## Visão Geral

A API utiliza **JWT (JSON Web Token)** para autenticação. Isso significa que o servidor não mantém estado de sessão (cookies). O cliente é responsável por armazenar o token e enviá-lo em cada requisição.

## Fluxo de Autenticação

### 1. Login

Faça uma requisição `POST` para `/login` com as credenciais do usuário.

**Requisição:**
```javascript
const response = await fetch('http://localhost:5000/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: 'usuario@exemplo.com',
        password: 'senha123'
    })
});
```

**Resposta de Sucesso (200 OK):**
```json
{
    "message": "Login successful",
    "user": {
        "id": 1,
        "username": "usuario",
        "email": "usuario@exemplo.com",
        "is_admin": false
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..." 
}
```

### 2. Armazenamento do Token

Ao receber a resposta de sucesso, extraia o `access_token` e armazene-o de forma segura no cliente.

**Exemplo (localStorage):**
```javascript
const data = await response.json();
localStorage.setItem('token', data.access_token);
localStorage.setItem('user', JSON.stringify(data.user));
```

### 3. Requisições Autenticadas

Para acessar rotas protegidas (como `/api/evaluations` ou `/api/dashboard`), você deve incluir o token no cabeçalho `Authorization` com o prefixo `Bearer`.

**Exemplo:**
```javascript
const token = localStorage.getItem('token');

const response = await fetch('http://localhost:5000/api/evaluations', {
    method: 'GET',
    headers: {
        'Authorization': `Bearer ${token}`, // IMPORTANTE: Espaço após 'Bearer'
        'Content-Type': 'application/json'
    }
});

if (response.status === 401) {
    // Token expirado ou inválido -> Redirecionar para login
    logout();
}
```

### 4. Logout

Como a autenticação é stateless (sem estado no servidor), o "logout" é feito simplesmente removendo o token do armazenamento do cliente.

**Exemplo:**
```javascript
function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
}
```

## Tratamento de Erros

*   **401 Unauthorized:** O token não foi enviado, é inválido ou expirou. O frontend deve redirecionar o usuário para a tela de login.
*   **403 Forbidden:** O usuário está autenticado, mas não tem permissão para acessar o recurso (ex: rota apenas para admins).

## Exemplo com Axios

Se estiver usando Axios, você pode configurar um interceptor para adicionar o token automaticamente:

```javascript
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:5000'
});

api.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
```
