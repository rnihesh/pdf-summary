import 'package:flutter/material.dart';

import 'auth_store.dart';
import 'screens/library.dart';
import 'screens/login.dart';
import 'theme.dart';

void main() {
  runApp(const App());
}

class App extends StatelessWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PDF Summary',
      theme: buildTheme(),
      debugShowCheckedModeBanner: false,
      home: const _Boot(),
    );
  }
}

class _Boot extends StatefulWidget {
  const _Boot();
  @override
  State<_Boot> createState() => _BootState();
}

class _BootState extends State<_Boot> {
  Widget? _next;

  @override
  void initState() {
    super.initState();
    _decide();
  }

  Future<void> _decide() async {
    final auth = await AuthStore.load();
    if (!mounted) return;
    setState(() {
      _next = auth.token != null ? const LibraryScreen() : const LoginScreen();
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_next == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    return _next!;
  }
}
