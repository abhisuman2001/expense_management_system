import React from 'react';
import { Container, Typography } from '@mui/material';

const Approvals = () => {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Pending Approvals
      </Typography>
      <Typography>
        This page will show expenses waiting for approval with approve/reject actions.
      </Typography>
    </Container>
  );
};

export default Approvals;