import React from 'react';
import { Container, Typography } from '@mui/material';

const Expenses = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        My Expenses
      </Typography>
      <Typography>
        This page will show a table of all expenses with filtering and search capabilities.
      </Typography>
    </Container>
  );
};

export default Expenses;