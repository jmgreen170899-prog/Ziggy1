# Ziggy UI Design System

A comprehensive design system for the Ziggy platform featuring dark-first themes, semantic tokens, and accessible components.

## Design Principles

- **Dark-first:** Optimized for dark mode with light mode support
- **Semantic:** Meaningful color and spacing tokens
- **Accessible:** WCAG AA compliant with proper focus management
- **Consistent:** Unified patterns across all components
- **Professional:** Clean, modern aesthetic suitable for financial platforms

## Design Tokens

### Color System

| Token           | Dark Value | Light Value | Usage              |
| --------------- | ---------- | ----------- | ------------------ |
| `--fg`          | #e4e4e7    | #18181b     | Primary text       |
| `--fg-muted`    | #a1a1aa    | #52525b     | Secondary text     |
| `--bg`          | #09090b    | #ffffff     | Primary background |
| `--bg-elevated` | #18181b    | #f4f4f5     | Cards, panels      |
| `--border`      | #27272a    | #e4e4e7     | Default borders    |
| `--accent`      | #00ff88    | #00ff88     | Brand color        |

### Spacing System (8px grid)

| Token   | Value | Usage           |
| ------- | ----- | --------------- |
| space-1 | 4px   | Tight spacing   |
| space-2 | 8px   | Small gaps      |
| space-4 | 16px  | Default spacing |
| space-6 | 24px  | Section spacing |
| space-8 | 32px  | Large spacing   |

## Component Library

### Buttons

```jsx
import Button from "@/components/ui/Button";

// Variants: primary, secondary, ghost, destructive, link, outline
// Sizes: sm, md, lg, icon
<Button variant="primary" size="md" loading={isLoading}>
  Save Changes
</Button>;
```

### Cards

```jsx
import Card, { CardHeader, CardTitle, CardContent } from "@/components/ui/Card";

<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>Content here</CardContent>
</Card>;
```

### Form Inputs

```jsx
import Input from '@/components/ui/Input';
import Select, { SelectOption } from '@/components/ui/Select';

<Input
  label="Email"
  required
  error={errors.email}
  hint="We'll never share your email"
/>

<Select label="Country" placeholder="Select country">
  <SelectOption value="us">United States</SelectOption>
  <SelectOption value="ca">Canada</SelectOption>
</Select>
```

### Badges

```jsx
import Badge from '@/components/ui/Badge';

// Variants: default, secondary, destructive, outline, success, warning, info
<Badge variant="success">Active</Badge>
<Badge variant="warning">Pending</Badge>
<Badge variant="destructive">Error</Badge>
```

### Data Tables

```jsx
import { DataTable } from "@/components/ui/Table";

const columns = [
  { key: "name", header: "Name", sortable: true },
  { key: "status", header: "Status" },
];

<DataTable data={users} columns={columns} sortable pagination pageSize={10} />;
```

### Dialogs

```jsx
import Dialog, { DialogFooter } from "@/components/ui/Dialog";

<Dialog open={isOpen} onClose={handleClose} title="Confirm Action">
  <DialogFooter>
    <Button variant="ghost">Cancel</Button>
    <Button variant="destructive">Delete</Button>
  </DialogFooter>
</Dialog>;
```

### Toast Notifications

```jsx
import { useToast } from "@/components/ui/ToastProvider";

const { success, error, warning } = useToast();

success("Settings saved!");
error("Failed to save");
warning("This will overwrite data");
```

### Theme System

```jsx
import { ThemeToggle, ThemeSelector } from '@/components/ui/ThemeToggle';

// Simple toggle
<ThemeToggle />

// Full selector with system option
<ThemeSelector />
```

### Loading States

```jsx
import Skeleton, { SkeletonCard } from '@/components/ui/Skeleton';

<Skeleton variant="text" />
<Skeleton variant="avatar" />
<SkeletonCard includeHeader lines={3} />
```

## Best Practices

### Colors

- Use semantic tokens: `bg-bg`, `text-fg`, `border-border`
- Never hard-code colors: ❌ `#000000` → ✅ `var(--bg)`
- Use CSS variables for consistency

### Spacing

- Follow 8px grid: `space-2` (8px), `space-4` (16px), `space-6` (24px)
- Use consistent spacing classes: `p-4`, `m-6`, `gap-2`

### Typography

- Use semantic font sizes: `text-sm`, `text-base`, `text-lg`
- Apply consistent line heights and spacing

### Accessibility

- Include ARIA labels: `aria-label="Close dialog"`
- Use semantic HTML: `<button>`, `<input>`, `<select>`
- Ensure keyboard navigation works
- Test with screen readers

### Responsive Design

- Mobile-first approach: `sm:`, `md:`, `lg:` prefixes
- Use responsive spacing and typography
- Test across all breakpoints

## Usage Examples

### Dashboard Card

```jsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between">
    <CardTitle>Revenue</CardTitle>
    <Badge variant="success">+12%</Badge>
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">$45,678</div>
    <p className="text-sm text-fg-muted">From last month</p>
  </CardContent>
</Card>
```

### Form with Validation

```jsx
<Card>
  <CardHeader>
    <CardTitle>User Profile</CardTitle>
  </CardHeader>
  <CardContent className="space-y-4">
    <Input label="Display Name" required error={errors.name} />
    <Select label="Role" required>
      <SelectOption value="admin">Administrator</SelectOption>
      <SelectOption value="user">User</SelectOption>
    </Select>
  </CardContent>
  <CardFooter>
    <Button variant="primary" loading={isSubmitting}>
      Save Changes
    </Button>
  </CardFooter>
</Card>
```

### Data List with Actions

```jsx
<Card>
  <CardHeader>
    <CardTitle>Users ({users.length})</CardTitle>
  </CardHeader>
  <CardContent>
    <DataTable
      data={users}
      columns={[
        { key: "name", header: "Name", sortable: true },
        { key: "email", header: "Email" },
        {
          key: "status",
          header: "Status",
          render: (status) => (
            <Badge variant={status === "active" ? "success" : "secondary"}>
              {status}
            </Badge>
          ),
        },
      ]}
      sortable
      pagination
    />
  </CardContent>
</Card>
```

For complete documentation and migration guide, see [MIGRATION.md](./MIGRATION.md).
