import React from 'react';
import { Container, Typography } from '@mui/material';

const Users = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        User Management
      </Typography>
      <Typography>
        This page will allow admins to create, edit, and manage users and their roles.
      </Typography>
    </Container>
  );
};

export default Users;