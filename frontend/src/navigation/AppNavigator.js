import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import LoginScreen from '../screens/login';
import RegisterScreen from '../screens/register';
import ProjectsScreen from '../screens/projects';
import VideoCaptureScreen from '../screens/video_capture';
import ResultsScreen from '../screens/results';
import ReportsScreen from '../screens/reports';
import SetupScreen from '../screens/setup';
import UserManualScreen from '../screens/user_manual';
import { ROUTES } from './routes';

const Stack = createNativeStackNavigator();

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={ROUTES.LOGIN} screenOptions={{ headerShown: false }}>
        <Stack.Screen name={ROUTES.LOGIN} component={LoginScreen} />
        <Stack.Screen name={ROUTES.REGISTER} component={RegisterScreen} />
        <Stack.Screen name={ROUTES.PROJECTS} component={ProjectsScreen} options={{ headerShown: true, title: 'Proyectos' }} />
        <Stack.Screen name={ROUTES.VIDEO_CAPTURE} component={VideoCaptureScreen} options={{ headerShown: true, title: 'Captura de video' }} />
        <Stack.Screen name={ROUTES.RESULTS} component={ResultsScreen} options={{ headerShown: true, title: 'Resultados' }} />
        <Stack.Screen name={ROUTES.REPORTS} component={ReportsScreen} options={{ headerShown: true, title: 'Reportes' }} />
        <Stack.Screen name={ROUTES.SETUP} component={SetupScreen} options={{ headerShown: true, title: 'Configuracion' }} />
        <Stack.Screen name={ROUTES.USER_MANUAL} component={UserManualScreen} options={{ headerShown: true, title: 'Manual de usuario' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
