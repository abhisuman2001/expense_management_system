import React from 'react';
import { Container, Typography } from '@mui/material';

const SubmitExpense = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Submit New Expense
      </Typography>
      <Typography>
        This page will contain a form to submit new expenses with OCR receipt scanning.
      </Typography>
    </Container>
  );
};

export default SubmitExpense;