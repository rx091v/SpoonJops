import { Paper, Stack, Typography } from '@mui/material';

type PlaceholderPageProps = {
  title: string;
};

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <Stack spacing={2}>
      <Typography variant="h4" sx={{ fontWeight: 700 }}>
        {title}
      </Typography>
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography color="text.secondary">
          This workspace is reserved for the corresponding implementation phase.
        </Typography>
      </Paper>
    </Stack>
  );
}
